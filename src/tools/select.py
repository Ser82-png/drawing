# select.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import ToolTemplate

class ToolSelect(ToolTemplate):
	__gtype_name__ = 'ToolSelect'

	use_options = False # TODO

	def __init__(self, window, **kwargs):
		super().__init__('select', _("Selection"), 'edit-select-symbolic', window)

		self.x_press = 0.0
		self.y_press = 0.0
		self.past_x = [-1, -1]
		self.past_y = [-1, -1]

		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/tools/ui/select.ui")
		menu_r = builder.get_object("right-click-menu")
		self.rightc_popover = Gtk.Popover.new_from_model(self.window.drawing_area, menu_r)
		menu_l = builder.get_object("left-click-menu")
		self.selection_popover = Gtk.Popover.new_from_model(self.window.drawing_area, menu_l)

		#############################

		# Building the widget containing options
		self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)

		self.options_box.add(Gtk.Label(label=_("Selection type:")))
		btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		btn_box.get_style_context().add_class('linked')

		radio_btn = Gtk.RadioButton(draw_indicator=False, label=_("Rectangle"))
		radio_btn2 = Gtk.RadioButton(group=radio_btn, draw_indicator=False, label=_("Freehand"))
		radio_btn3 = Gtk.RadioButton(group=radio_btn, draw_indicator=False, label=_("Same color"))

		radio_btn.connect('clicked', self.on_option_changed)
		radio_btn2.connect('clicked', self.on_option_changed)
		radio_btn3.connect('clicked', self.on_option_changed)

		btn_box.add(radio_btn)
		btn_box.add(radio_btn2)
		btn_box.add(radio_btn3)

		radio_btn.set_active(True)
		self.selected_type_label = _("Rectangle")

		self.options_box.add(btn_box)

	def get_row(self):
		return self.row

	def on_option_changed(self, b):
		self.selected_type_label = b.get_label()

	def get_options_widget(self):
		return self.options_box

	def get_options_label(self):
		return self.selected_type_label

	def give_back_control(self):
		print('selection give back control')
		self.window._pixbuf_manager.show_selection_content()
		self.apply_to_pixbuf()
		self.end_selection()

	def show_popover(self, state):
		self.selection_popover.popdown()
		self.rightc_popover.popdown()
		if self.window._pixbuf_manager.selection_is_active and state:
			self.selection_popover.popup()
		elif state:
			self.rightc_popover.popup()

	def on_key_on_area(self, area, event, surface):
		print("key")
		# TODO

	def on_motion_on_area(self, area, event, surface):
		pass

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		print("press")
		self.window_can_take_back_control = False
		area.grab_focus()
		self.x_press = event.x
		self.y_press = event.y
		self.left_color = left_color
		self.right_color = right_color

	def on_release_on_area(self, area, event, surface):
		print("release") # TODO à main levée c'est juste un crayon avec close_path() après
		primary_color = ''
		secondary_color = ''
		if event.button == 3:
			rectangle = Gdk.Rectangle()
			rectangle.x = int(event.x)
			rectangle.y = int(event.y)
			rectangle.height = 1
			rectangle.width = 1
			self.rightc_popover.set_pointing_to(rectangle)
			self.rightc_popover.set_relative_to(area)
			self.show_popover(True)
			return
		else:
			# If nothing is selected (only -1), coordinates should be memorized, but
			# if something is already selected, the selection should be cancelled (the
			# action is performed outside of the current selection), or stay the same
			# (the user is moving the selection by dragging it).
			if self.past_x[0] == -1:
				self.past_x[0] = event.x
				self.past_x[1] = self.x_press
				self.past_y[0] = event.y
				self.past_y[1] = self.y_press
				print('cas mémorisation, on continue la fonction')
				self.selection_popover.set_relative_to(area)
				self.create_selection_from_coord()
				self.draw_selection_area()
			elif self.point_is_in_selection(self.x_press, self.y_press):
				print('cas où faut bouger')
				self.drag_to(event.x, event.y)
				return
			else:
				print('cas autre')
				self.window._pixbuf_manager.show_selection_content()
				self.apply_to_pixbuf()
				self.end_selection()
				return

	def point_is_in_selection(self, x, y):
		if x < self.window._pixbuf_manager.selection_x:
			return False
		elif y < self.window._pixbuf_manager.selection_y:
			return False
		elif x > self.window._pixbuf_manager.selection_x + \
		self.window._pixbuf_manager.selection_pixbuf.get_width():
			return False
		elif y > self.window._pixbuf_manager.selection_y + \
		self.window._pixbuf_manager.selection_pixbuf.get_height():
			return False
		else:
			return True

	def get_center_of_selection(self):
		x = self.window._pixbuf_manager.selection_x + \
		self.window._pixbuf_manager.selection_pixbuf.get_width()/2
		y = self.window._pixbuf_manager.selection_y + \
		self.window._pixbuf_manager.selection_pixbuf.get_height()/2
		return [x, y]

	def create_selection_from_coord(self):
		x0 = self.past_x[0]
		x1 = self.past_x[1]
		y0 = self.past_y[0]
		y1 = self.past_y[1]
		if self.past_x[0] > self.past_x[1]:
			x0 = self.past_x[1]
			x1 = self.past_x[0]
		if self.past_y[0] > self.past_y[1]:
			y0 = self.past_y[1]
			y1 = self.past_y[0]
		self.window._pixbuf_manager.create_selection_from_main(x0, y0, x1, y1)

	def draw_selection_area(self):
		self.window._pixbuf_manager.show_selection_rectangle()
		rectangle = Gdk.Rectangle()
		[rectangle.x, rectangle.y] = self.get_center_of_selection()
		rectangle.height = 1
		rectangle.width = 1
		self.selection_popover.set_pointing_to(rectangle)
		self.show_popover(True)

	def end_selection(self):
		self.show_popover(False)
		self.window_can_take_back_control = True
		self.x_press = 0.0
		self.y_press = 0.0
		self.past_x = [-1, -1]
		self.past_y = [-1, -1]

	def drag_to(self, final_x, final_y):
		self.restore_pixbuf()
		delta_x = final_x - self.x_press
		delta_y = final_y - self.y_press
		self.past_x[0] += delta_x
		self.past_x[1] += delta_x
		self.past_y[0] += delta_y
		self.past_y[1] += delta_y
		self.window._pixbuf_manager.selection_x += delta_x
		self.window._pixbuf_manager.selection_y += delta_y
		self.window._pixbuf_manager.show_selection_rectangle()

