class Order:
    def _init_(self, cargo, start_point, end_point, price, comment):
        self.cargo = cargo
        self.start_point = start_point
        self.end_point = end_point
        self.price = price
        self.comment = comment


class User:
    def _init_(self, first_name, last_name, phone_number):
        self.first_name=first_name
        self.last_name=last_name
        self.phone_number = phone_number
