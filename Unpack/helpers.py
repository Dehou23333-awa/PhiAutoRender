import pez

def PezHelper(track_id, level_name, type):
    pez.create_pez(track_id, level_name, type)
    if level_name == 'IN' or level_name == 'AT':
        pez.create_pez(track_id, level_name, type)
        pez.create_pez(track_id, level_name, type, Ratio="4:3")
        pez.create_pez(track_id, level_name, type, isDebug=True)
