import simplespotify as ss

auth = ss.client()
auth.use_client_credentials()

search = input("Enter an album search : ")

alb = ss.album.from_search(search)

if alb is not None :
	
	print("")
	print("{: ^120}".format("+" + "{:-^48}".format(alb.name + " by " + alb.artists[0].name ) + "+"))
	print("{: ^120}".format("|"+" "*48+"|"))

	for trk in alb.tracks :
		print("{: ^120}".format("|"+ "{: ^48}".format(trk.name) + "|"))

	print("{: ^120}".format("|"+" "*48+"|"))
	print("{: ^120}".format("+"+"-"*48+"+"))
	print("")

else :
	print("Couldn't Find Album")