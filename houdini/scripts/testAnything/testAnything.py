import hou

def testAnything():
    print('Hello World')

def run():
    # Define the dropdown menu options
    items = ["Option 1", "Option 2", "Option 3"]
    
    # Show the dropdown dialog
    choice = hou.ui.selectFromList(items, exclusive=True, title="Choose an Option", message="Please select an option:")
    
    # Check if the user made a choice
    if choice:
        selected_item = items[choice[0]]
        print("You selected:", selected_item)
    else:
        print("No option was selected.")


if __name__ != "__main__":
    #code executé si lancé en tant que module
    # Exemple d'utilisation
    print("\n\n-- New Exec -- testAnything \n\n")



