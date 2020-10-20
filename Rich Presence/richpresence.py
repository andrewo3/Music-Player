import pypresence,os,time

client_id = 737918274548924446
client=pypresence.Presence(client_id)
client.connect()
client.clear()
client.update(os.getpid(),"Bruh Moment","n word lol",time.time(),time.time()+10)
time.sleep(10)
client.clear()
client.close()