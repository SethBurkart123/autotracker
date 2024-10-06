class LedController:
    def __init__(self, ser):
        self.ser = ser
        self.LED_LUT = [
            [4, 3, 2, 1, 0],
            [9, 8, 7, 6, 5],
            [14, 13, 12, 11, 10],
            [None, None, 17, 16, 15]
        ]
        self.LED_STATE = [
            [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]],
            [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]],
            [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]],
            [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]]
        ]
        self.LED_TEMP = [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]]

    def show(self):
        for x in range(5):
            for y in range(4):
                if self.LED_LUT[y][x] != None:
                    self.LED_TEMP[self.LED_LUT[y][x]] = self.LED_STATE[y][x]
        # Convert the list of lists into a flat list
        temp_list = [item for sublist in self.LED_TEMP for item in sublist]
        #print(temp_list)
        binary_data = bytes(temp_list)
        self.ser.write(binary_data[:-6]) #idk why -6 bytes????
    
    def update(self, x, y, rgb):
        self.LED_STATE[x][y] = rgb