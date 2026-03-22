import pygame
import numpy as np

control_Length = 1 + 7 + 3

def remote_control():
    FH = 0xA5
    Value = []
    pygame.init()
    pygame.joystick.init()

    try:
        # 检查是否有可用的遥控器
        if pygame.joystick.get_count() == 0:
            # 如果没有遥控器，返回全 0 的列表
            Value = [0] * (control_Length - 1)
            Value.insert(0, FH)
            return Value

        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        # name = joystick.get_name()
        # Value.append(name)

        for i in range(8):
            axis = joystick.get_axis(i)
            if i < 4:  # 这是几个摇杆
                axis = round(map(axis, -1, 1, 0, 255))
            elif i == 4:  # 滚轮
                axis = round(map(axis, -0.93, 0.95, 0, 255))
                if axis < 0:
                    axis = 0
                elif axis > 255:
                    axis = 255
            else:  # 按键
                if axis < -0.5:
                    axis = 0
                elif -0.5 <= axis <= 0.5:
                    axis = 1
                elif axis > 0.5:
                    axis = 2
            Value.append(axis)

        for i in range(3):
            button = joystick.get_button(i)
            Value.append(button)
        Value.insert(0, FH)

    except pygame.error:
        # 如果在操作过程中出现错误（如遥控器拔掉），返回全 0 的列表
        Value = [0] * (control_Length - 1)
        Value.insert(0, FH)

    return Value


def map(data, d_min, d_max, MIN, MAX):
    """
    归一化映射到任意区间

    :param MIN: 目标数据最小值
    :param MAX: 目标数据最小值
    :return:
    """
    return MIN + (MAX - MIN) / (d_max - d_min) * (data - d_min)


if __name__ == "__main__":

    # Define some colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)


    # This is a simple class that will help us print to the screen
    # It has nothing to do with the joysticks, just outputting the
    # information.
    class TextPrint:
        def __init__(self):
            self.reset()
            self.font = pygame.font.Font(None, 25)

        def print(self, screen, textString):
            textBitmap = self.font.render(textString, True, BLACK)
            screen.blit(textBitmap, [self.x, self.y])
            self.y += self.line_height

        def reset(self):
            self.x = 10
            self.y = 10
            self.line_height = 15

        def indent(self):
            self.x += 10

        def unindent(self):
            self.x -= 10


    pygame.init()

    # Set the width and height of the screen [width,height]
    size = [400, 300]
    screen = pygame.display.set_mode(size)

    pygame.display.set_caption("My Game")

    # Loop until the user clicks the close button.
    done = False

    # Used to manage how fast the screen updates
    clock = pygame.time.Clock()

    # Initialize the joysticks
    pygame.joystick.init()

    # Get ready to print
    textPrint = TextPrint()

    # -------- Main Program Loop -----------
    while done == False:
        # EVENT PROCESSING STEP
        for event in pygame.event.get():  # User did something
            if event.type == pygame.QUIT:  # If user clicked close
                done = True  # Flag that we are done so we exit this loop

            # Possible joystick actions: JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
            if event.type == pygame.JOYBUTTONDOWN:
                print("Joystick button pressed.")
            if event.type == pygame.JOYBUTTONUP:
                print("Joystick button released.")

        # DRAWING STEP
        # First, clear the screen to white. Don't put other drawing commands
        # above this, or they will be erased with this command.
        screen.fill(WHITE)
        textPrint.reset()

        # Get count of joysticks
        joystick_count = pygame.joystick.get_count()

        textPrint.print(screen, "Number of joysticks: {}".format(joystick_count))
        textPrint.indent()

        # For each joystick:
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()

            textPrint.print(screen, "Joystick {}".format(i))
            textPrint.indent()

            # Get the name from the OS for the controller/joystick
            name = joystick.get_name()
            textPrint.print(screen, "Joystick name: {}".format(name))

            # Usually axis run in pairs, up/down for one, and left/right for
            # the other.
            axes = joystick.get_numaxes()
            textPrint.print(screen, "Number of axes: {}".format(axes))
            textPrint.indent()

            for i in range(axes):
                axis = joystick.get_axis(i)
                textPrint.print(screen, "Axis {} value: {:>6.3f}".format(i, axis))
            textPrint.unindent()

            buttons = joystick.get_numbuttons()
            textPrint.print(screen, "Number of buttons: {}".format(buttons))
            textPrint.indent()

            for i in range(buttons - 21):
                button = joystick.get_button(i)
                textPrint.print(screen, "Button {:>2} value: {}".format(i, button))
            textPrint.unindent()

            # Hat switch. All or nothing for direction, not like joysticks.
            # Value comes back in an array.
            hats = joystick.get_numhats()
            textPrint.print(screen, "Number of hats: {}".format(hats))
            textPrint.indent()

            for i in range(hats):
                hat = joystick.get_hat(i)
                textPrint.print(screen, "Hat {} value: {}".format(i, str(hat)))
            textPrint.unindent()

            textPrint.unindent()

        # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT

        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

        # Limit to 20 frames per second
        clock.tick(50)

    # Close the window and quit.
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()

