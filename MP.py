import socket
import hashlib
import struct
import threading
import json
import secrets
from constants import LOBBY_PORT, LOBBY_START_ACK, LOBBY_START_VOTE, BLANK, T_LOBBY_TIMEOUT, T_LOBBY_ANNOUNCE_INTERVAL, LOBBY_PRESENCE, SENTINEL, MIN_PLAYERS, MAX_PLAYERS, LOBBY_LEAVE, T_LOBBY_STALE, T_LOBBY_QUIET
from collections import defaultdict
from states import State
import time

GAME_PORT = 0
listening = True


def make_session_id(thing): 
    id = hashlib.sha256(thing.encode("utf-8")).digest()
    return id[:16]

def build_packet(msgtype, sesID, sendID, another_thing, flags, SEQ, ACK):
    if another_thing is None:
        body = b""
    else:
        body = json.dumps(another_thing).encode("utf-8")

    header = struct.pack('!BBBB16sHHII', 1, msgtype, flags, 0, sesID, sendID, len(body), SEQ, ACK)
    full_message = header + body

    if len(full_message) > 1200:
        raise ValueError("Message is too long.")
    else:
        return full_message

def send_broadcast(s, username, lobby_self_id, hashed, ip):
    message_body = { 
        "lobby_peer_id": lobby_self_id,
        "display_name": username,
        "host": ip,
        "port": s.getsockname()[1]}
    full_message = build_packet(LOBBY_PRESENCE, hashed, SENTINEL, message_body, 0, 0, 0)
    s.sendto(full_message, ("255.255.255.255", LOBBY_PORT))

def send_leave(s, lobby_self_id, hashed):
    message_body = { "lobby_peer_id": lobby_self_id }
    full_message = build_packet(LOBBY_LEAVE, hashed, SENTINEL, message_body, 0, 0, 0)
    s.sendto(full_message, ("255.255.255.255", LOBBY_PORT))

def send_vote(s, hashed, roster):
    message_body = { "participants": sorted(roster.keys())}
    full_message = build_packet(LOBBY_START_VOTE, hashed, SENTINEL, message_body, 0, 0, 0)
    s.sendto(full_message, ("255.255.255.255", LOBBY_PORT))

def send_vote_ack(s, hashed, hashed_participants):
    message_body = { "participants_hash": hashed_participants }
    full_message = build_packet(LOBBY_START_ACK, hashed, SENTINEL, message_body, 0, 0, 0)
    s.sendto(full_message, ("255.255.255.255", LOBBY_PORT))

def hash_participants(peer_list):
    canonical_list = json.dumps(sorted(peer_list), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical_list).hexdigest()
        
def unpack_packet(daMessage):
    if len(daMessage) < 32:
        return None
    else:
        decodedHeader = struct.unpack('!BBBB16sHHII', daMessage[:32])
        if decodedHeader[0] != 1 or ((decodedHeader[6] + 32) != len(daMessage)):
            return None
        else:
            if decodedHeader[6] == 0:
                return decodedHeader, {} 
            try:
                decodedBody = json.loads(daMessage[32:])
                if isinstance(decodedBody, dict):
                    return decodedHeader, decodedBody 
                else:
                    return None
            except ValueError:
                return None       

done = False

l =  socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    l.connect(("8.8.8.8", 80))
    ip_address = l.getsockname()[0]
except Exception:
    ip_address = "127.0.0.1"
finally:
    l.close()

while not done:
    state = State.IDLE
    username = input("Enter your IGN (in game name): ")
    lobby_name = input("Enter the lobby name: ")
    hashed = make_session_id(lobby_name)
    roster = defaultdict(list)
    sorted_peers = None
    acks_received = set()
    active_hash = None

    if(lobby_name != None):
        state = State.LOBBY_SEARCHING

        #making the listening socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.2)
        sock.bind((BLANK, LOBBY_PORT))

        #making the gaming socket
        game = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        game.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        game.bind(("", 0))

        #making of id and roster
        lobby_self_id = secrets.token_hex(16)
        roster[lobby_self_id] = [username, ip_address, game.getsockname()[1], None]

        #sending a LOBBY_PRESENCE
        timer = time.perf_counter()
        last_sent = 0.0
        last_vote_sent = 0.0
        last_roster_change = timer

        while(time.perf_counter() - timer) <= T_LOBBY_TIMEOUT and state == State.LOBBY_SEARCHING:
            #broadcasting section
            present = time.perf_counter()
            if present - last_sent >= T_LOBBY_ANNOUNCE_INTERVAL:
                send_broadcast(game, username, lobby_self_id, hashed, ip_address)
                print("Searching for players....")
                last_sent = present

            #listening section
            try:
                data, addr = sock.recvfrom(1200)
                received = unpack_packet(data)
                if received == None:
                    pass
                else:
                    last_heard = time.perf_counter()
                    header, body = received
                    
                    ver, msgType, flags, res, sesID, sendID, bodyLen, seqn, ackn = header
                    
                    if hashed == sesID and msgType == LOBBY_PRESENCE:
                        new_peer = body["lobby_peer_id"]
                        if new_peer != lobby_self_id:
                            is_new = new_peer not in roster
                            roster[new_peer] = [body["display_name"], body["host"], body["port"], last_heard]
                            if is_new:
                                print(f"{roster[new_peer][0]} joined.")
                                last_roster_change = time.perf_counter()
                                active_hash = None
                                acks_received.clear()

                    if hashed == sesID and msgType == LOBBY_START_VOTE:
                        peer_list = body["participants"]
                        if sorted(roster.keys()) == peer_list:
                            hashed_participants = hash_participants(peer_list)
                            send_vote_ack(game, hashed, hashed_participants)
                            if active_hash != hashed_participants:
                                acks_received = {lobby_self_id}
                                active_hash = hash_participants(sorted(roster.keys()))
                            peer_key = next((k for k, v in roster.items() if addr == (v[1], v[2])), None)
                            if peer_key != None and roster.get(peer_key)[2] == addr[1]:
                                acks_received.add(lobby_self_id)
                                acks_received.add(peer_key)
                            if acks_received == set(roster.keys()):
                                state = State.INIT
                                sock.close()
                            
                                

                    if hashed == sesID and msgType == LOBBY_LEAVE and body.get("lobby_peer_id") != lobby_self_id:
                        if roster.pop(body.get("lobby_peer_id"), None) != None:
                            acks_received.clear()
                            active_hash = None
                            last_vote_sent = 0.0
                            last_roster_change = time.perf_counter()

                    if hashed == sesID and msgType == LOBBY_START_ACK:
                        if active_hash == body.get("participants_hash"):
                            active_hash = body.get("participants_hash")
                            peer_key = next((k for k, v in roster.items() if addr == (v[1], v[2])), None)
                            if peer_key != None and roster.get(peer_key)[2] == addr[1]:
                                acks_received.add(lobby_self_id)
                                acks_received.add(peer_key)
                        if acks_received == set(roster.keys()):
                            state = State.INIT
                            sock.close()  

            except socket.timeout:
                pass
            except OSError:
                print("Something went wrong")
                continue

            #removing stale peers
            peerCheck = time.perf_counter()
            dup_roster = roster.copy()
            for key, value in dup_roster.items():
                if key != lobby_self_id and peerCheck - value[3] >= T_LOBBY_STALE:
                    last_roster_change = peerCheck
                    acks_received.clear()
                    last_vote_sent = 0.0
                    active_hash = None
                    del roster[key]

            #minimum 3 players
            if MIN_PLAYERS <= len(roster) <= MAX_PLAYERS:
                if time.perf_counter() - last_roster_change >= T_LOBBY_QUIET:
                    sorted_peers = sorted(roster.keys())
                    print("Minimum player count met, initiate voting.")
                    if (time.perf_counter() - last_vote_sent >= T_LOBBY_QUIET):
                        last_vote_sent = time.perf_counter()
                        if active_hash != hash_participants(sorted_peers):
                            active_hash = hash_participants(sorted_peers)
                            acks_received = {lobby_self_id}
                        send_vote(game, hashed, roster)

        #T_LOBBY_TIMEOUT is hit
        if state == State.LOBBY_SEARCHING:
            if len(roster) >= MIN_PLAYERS and len(roster) <= MAX_PLAYERS:
                active_hash = hash_participants(sorted(roster.keys()))
                acks_received = {lobby_self_id}
                send_vote(game, hashed, roster)
                last_vote_sent = time.perf_counter()
                print("Final call")
                final_timer = time.perf_counter()
                while (time.perf_counter() - final_timer) <= T_LOBBY_QUIET and state == State.LOBBY_SEARCHING:
                    try:
                        data, addr = sock.recvfrom(1200)
                        received = unpack_packet(data)
                        if received == None:
                            pass
                        else:
                            last_heard = time.perf_counter()
                            header, body = received
                                            
                            ver, msgType, flags, res, sesID, sendID, bodyLen, seqn, ackn = header
                            if hashed == sesID and msgType == LOBBY_START_VOTE:
                                peer_list = body["participants"]
                                if sorted(roster.keys()) == peer_list:
                                    hashed_participants = hash_participants(peer_list)
                                    send_vote_ack(game, hashed, hashed_participants)
                                    if active_hash != hashed_participants:
                                        acks_received = {lobby_self_id}
                                        active_hash = hash_participants(sorted(roster.keys()))
                                    peer_key = next((k for k, v in roster.items() if addr == (v[1], v[2])), None)
                                    if peer_key != None and roster.get(peer_key)[2] == addr[1]:
                                        acks_received.add(lobby_self_id)
                                        acks_received.add(peer_key)
                                    if acks_received == set(roster.keys()):
                                        state = State.INIT
                                        sock.close()

                            if hashed == sesID and msgType == LOBBY_START_ACK:
                                if active_hash == body.get("participants_hash"):
                                    active_hash = body.get("participants_hash")
                                    peer_key = next((k for k, v in roster.items() if addr == (v[1], v[2])), None)
                                    if peer_key != None and roster.get(peer_key)[2] == addr[1]:
                                        acks_received.add(lobby_self_id)
                                        acks_received.add(peer_key)
                                if acks_received == set(roster.keys()):
                                    state = State.INIT
                                    sock.close()
                    except socket.timeout:
                        pass
                    except OSError:
                        print("Something went wrong")
                        continue

        if state == State.LOBBY_SEARCHING:
            print("Left the lobby")
            send_leave(game, lobby_self_id, hashed)
            sock.close()
            game.close()
            state = State.IDLE
        if state == State.INIT:
            #future code
            print("thing")
print("End")