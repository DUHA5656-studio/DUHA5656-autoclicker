import time
import keyboard
import mouse

def change():
    global work
    work = not work

work = False

keyboard.add_hotkey('F7', change)

x = [1]

print("Включить ускорение? введите 1 если да, что-то другое если нет.")

a = int(input())
print("задайте интервал (только для обычного режима)")

b = [ float(input())]

if a == 1:
	while True:
		if work:              
			mouse.hold(button='left')    
			time.sleep(x[0])            
			mouse.release(button='left')               
			time.sleep(x[0])
			if x[0] >= 0.02:
				x[0]*=0.95
else:
	while True:
		if work:              
			mouse.hold(button='left')    
			time.sleep(b[0]/2)          
			mouse.release(button='left')               
			time.sleep(b[0]/2)       
