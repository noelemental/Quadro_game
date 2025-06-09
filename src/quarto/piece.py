class Piece:
    def __init__(self, height, solidity, shape, color):
        self.height = height  # True for tall, False for short
        self.solidity = solidity  # True for solid, False for hollow
        self.shape = shape  # True for square, False for circular
        self.color = color  # True for dark, False for light
        
    def __str__(self):
        attrs = []
        attrs.append('t' if self.height else 's')
        attrs.append('s' if self.solidity else 'h')
        attrs.append('s' if self.shape else 'c')
        attrs.append('d' if self.color else 'l')
        return '-'.join(attrs)
    
    def shares_attribute(self, other):
        if other is None:
            return False
        return (self.height == other.height or
                self.solidity == other.solidity or
                self.shape == other.shape or
                self.color == other.color)