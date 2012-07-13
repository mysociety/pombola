## Steps to import the representatives

Retrieve the full list from website:

    mkdir var
    cd var 
    curl -o all.html http://www.nassnig.org/nass2/Princ_officers_all.php?title_sur=Hon.

Extract from that a list of all the urls to the representative pages

    ../extract_representative_urls.py < all.html > representative_urls.txt

Get all the representative pages

    wget -i representative_urls.txt 

Process all the HTML and extract the relevant details:

    python ../representative_page_to_json.py profile.php*
