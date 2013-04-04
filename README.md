About
===
TF2Inventory is a tool for the popular online game [Team Fortress 2](http://store.steampowered.com/app/440/). Basically, within the game you have an inventory containing all your items. TF2Inventory consoliates the inventories of your accounts (if you have multiples), and displays them in a neatly formatted web page. This allows you to quickly view what items you have on which accounts. 

What's New
===

* Improved UI. Neater. Important information is now displayed more prominently.
* Integrated filter. No need for CTRL+F!
* Uses SQLite to store item data.
* Uses [Mako](http://www.makotemplates.org/) for templating.
* Uses [FooTable](http://themergency.com/footable/) for expandable rows and filtering.

Installation
===
The source code is publicly available on GitHub. As usual, you can either download a .zip from the link above or clone the repo to your local machine.

    > git clone https://github.com/wryyl/TF2Inventory.git

Configuration
===
Configure TF2Inventory using `config.ini`. 

* `accounts`: A comma-separated list of your TF2 accounts.
* `api_key`: Your API key. You can get your Steam API key [here](http://steamcommunity.com/dev/apikey). 
* `poll_minutes`: The frequency at which to update the HTML file.
* `html_dir`: The directory in which to generate the HTML file.
* `file_name`: The name of the generated HTML file.

To use TF2Inventory, simply run `TF2Inventory.py`.
