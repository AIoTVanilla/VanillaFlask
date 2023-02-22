CHICKEN_LEGS = "chicken_legs"
KANCHO = "kancho"
ROLLPOLY = "rollpoly"
RAMEN_SNACK = "ramen_snack"
WHALE_FOOD = "whale_food"

def get_snack_name():
    return {
        CHICKEN_LEGS: "닭다리",
        KANCHO: "칸쵸",
        ROLLPOLY: "롤리폴리",
        RAMEN_SNACK: "쫄병 안성탕면",
        WHALE_FOOD: "고래밥"
    }

def get_snack_color():
    return {
        CHICKEN_LEGS: "danger",
        KANCHO: "warning",
        ROLLPOLY: "muted",
        RAMEN_SNACK: "info",
        WHALE_FOOD: "success"
    }