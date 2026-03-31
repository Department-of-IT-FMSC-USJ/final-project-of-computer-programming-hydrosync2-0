import functions
import database


filtered = []

def get_counts():
    filtered = []
    while True:
        data = input("Enter species count (0 to stop): ")
        if data.isdigit():
            num = float(data)
            if num == 0:
                break
            elif num > 0:
                filtered.append(num)
            else:
                print("Enter a positive number.")
        else:
            print("Invalid input.")
    return filtered

def main_menu():
    while True:
        print("\nWater Quality Analysis Menu:")
        print("1. Shannon-Wiener Index")
        print("2. Pielou's Evenness")
        print("3. Simpson's Index of Diversity")
        print("4. Plankton Abundance")
        print("5. Margslef's Richness_Index")
        print("6. Exit")

        choice = input("Enter choice: ")
        if choice == '1':
            counts = get_counts()
            print("Shannon-Wiener Index:",functions.shannon_index(counts))
        elif choice == '2':
            counts = get_counts()
            print("Pielou's Evenness:", functions.pielou_evenness(counts))
        elif choice == '3':
            counts = get_counts()
            print("Simpson's Index of Diversity:", functions.simpson_diversity(counts))
        elif choice == '4':
            print("Plankton Abundance:", functions.plankton_abundance())

        elif choice == '5':
            counts = get_counts()
            print("Margslef's Richness_Index:", functions.richness_index(counts))

        elif choice == '6':
            print("Goodbye")
        else:
            print("Invalid option.")

main_menu()

