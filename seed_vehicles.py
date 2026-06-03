import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vehicle_rental.settings')
django.setup()

from rentals.models import Vehicle

def seed_data():
    vehicles_data = [
        {
            'name': 'Toyota Innova Crysta',
            'vehicle_type': 'car',
            'price_per_day': 3000.00,
            'image_path': 'innova_crysta.png',
            'mileage': '12.5 km/l',
            'fuel_type': 'Diesel',
            'description': 'The gold standard of luxury MPVs. Offers unmatched ride comfort, spacious 7-seater premium leather interior, and top-tier reliability for family trips.'
        },
        {
            'name': 'THAR ROXX',
            'vehicle_type': 'car',
            'price_per_day': 4000.00,
            'image_path': 'thar_roxx.png',
            'mileage': '15.2 km/l',
            'fuel_type': 'Diesel',
            'description': 'Mahindra Thar Roxx 4-door SUV. Dominate both highways and rough trails with a bold stance, modern digital cockpit, and ultimate 4x4 offroad capability.'
        },
        {
            'name': 'FORTUNER',
            'vehicle_type': 'car',
            'price_per_day': 3500.00,
            'image_path': 'fortuner.png',
            'mileage': '10.4 km/l',
            'fuel_type': 'Diesel',
            'description': 'Toyota Fortuner luxury SUV. Features a commanding design, extreme comfort, high durability, and power-packed performance on any highway tour.'
        },
        {
            'name': 'SWIFT',
            'vehicle_type': 'car',
            'price_per_day': 2500.00,
            'image_path': 'swift.png',
            'mileage': '22.3 km/l',
            'fuel_type': 'Petrol',
            'description': 'Suzuki Swift sporty hatchback. Fun-to-drive, fuel-efficient compact car with agile handling and sleek styling, ideal for city rentals and weekend cruises.'
        },
        {
            'name': 'Suzuki Ertiga',
            'vehicle_type': 'car',
            'price_per_day': 2800.00,
            'image_path': 'ertiga.png',
            'mileage': '20.5 km/l',
            'fuel_type': 'Petrol',
            'description': 'Suzuki Ertiga premium 7-seater MPV. Combining stylish design, advanced safety features, excellent fuel efficiency, and a highly versatile cabin for the perfect family getaway.'
        },
        {
            'name': 'Royal Enfield Classic 350',
            'vehicle_type': 'bike',
            'price_per_day': 500.00,
            'image_path': 're_classic.jpg',
            'mileage': '35.0 km/l',
            'fuel_type': 'Petrol',
            'description': 'The vintage machine. Iconic retro cruiser with timeless styling, signature thumping sound, and comfortable handling for premium long highway cruises.'
        },
        {
            'name': 'R15',
            'vehicle_type': 'bike',
            'price_per_day': 600.00,
            'image_path': 'r15.png',
            'mileage': '45.0 km/l',
            'fuel_type': 'Petrol',
            'description': 'Yamaha YZF R15 entry-level sportbike. Racing DNA, liquid-cooled engine, quick-shifter, and aggressive aerodynamics for unmatched tracks performance.'
        },
        {
            'name': 'KTM 390',
            'vehicle_type': 'bike',
            'price_per_day': 700.00,
            'image_path': 'ktm_390.png',
            'mileage': '30.0 km/l',
            'fuel_type': 'Petrol',
            'description': 'KTM Duke 390 street fighter. High power-to-weight ratio, naked street styling, aggressive torque, and supreme cornering agility for performance riders.'
        },
        {
            'name': 'MT 15',
            'vehicle_type': 'bike',
            'price_per_day': 650.00,
            'image_path': 'mt_15.png',
            'mileage': '45.0 km/l',
            'fuel_type': 'Petrol',
            'description': 'Yamaha MT-15 naked streetfighter. The Dark Warrior. Features a liquid-cooled 155cc engine, hyper-aggressive futuristic headlamp design, and light handling for city rides.'
        }
    ]

    print("Clearing old vehicle database records...")
    Vehicle.objects.all().delete()

    print("Checking database for existing vehicle entries...")
    for data in vehicles_data:
        vehicle, created = Vehicle.objects.get_or_create(
            name=data['name'],
            defaults={
                'vehicle_type': data['vehicle_type'],
                'price_per_day': data['price_per_day'],
                'image_path': data['image_path'],
                'mileage': data['mileage'],
                'fuel_type': data['fuel_type'],
                'description': data['description']
            }
        )
        if created:
            print(f"Added vehicle: {vehicle.name}")
        else:
            print(f"Vehicle already exists: {vehicle.name}")

    print("Database seeding completed.")

if __name__ == '__main__':
    seed_data()
