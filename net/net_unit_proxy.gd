extends Node
## Net -> RemotePlayer adapter: same peer_* signals as Net, but positions converted from JS world
## units (metres x 1.4205, what the server and the JS clients send) to Godot metres.
signal peer_joined(player: Dictionary)
signal peer_state(player: Dictionary)
signal peer_left(id: String)
