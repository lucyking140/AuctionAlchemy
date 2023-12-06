# AuctionAlchemy

This site was built from an original project for COMS 4111, Introduction to Databases, in collaboration with Alex Baril. The original project placed in the top 4 out of over 50 projects. All code currently used was written by Lucy King.

AuctionAlchemy provides a platform for users to create accounts and interact with our database of over 400 artists and 500 works of art sold in fine art auctions around the world. Users can like and follows works of art, artists, and auction houses that they enjoy, and will receive other recommended works to explore based on their interests. The site is developed with Flask and HTML/CSS, integrated with a PostgreSQL database used to query for recommendations, search functionality, and more. 

### Key features:
* Provides a comprehensive database of art pieces, which users can search based on Auction, Auction house, Location, Artist, Movement, and Medium
* Provides an automated summary of each auction and auction house based on frequently featured artists, movements, and regions highlighted
* Accounts for the sale of a work of art in multiple different auctions
* Users can “like” works, artists, auctions, auction houses, regions, movements, and follow specific auctions and auction houses   
* Users will receive recommendations for auctions and works based on their likes. The recommendation algorithm primarily takes liked works and auctions into account. If there are no liked works and auctions, it will pick works based upon liked movements and regions.
We find works and auctions to recommend by using the user's likes to find their most liked artists, movements, and regions, then finding other works in those categories that have not already been liked.

