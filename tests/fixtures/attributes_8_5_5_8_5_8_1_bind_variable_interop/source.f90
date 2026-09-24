module attributes_bind_variable_mod
  use iso_c_binding, only: c_int
  implicit none
  integer(c_int), bind(c) :: default_label_value = -1_c_int
  integer(c_int), bind(c, name="attr_bind_scalar") :: scalar_value = -2_c_int
  integer(c_int), bind(c, name="attr_bind_array") :: array_value(2:3) = [-3_c_int, -4_c_int]
  integer(c_int), bind(c, name="attr_bind_empty_array") :: empty_array(5:4)
  interface
    subroutine c_set_default(v) bind(c, name="c_set_default")
      import c_int
      integer(c_int), value :: v
    end subroutine
    integer(c_int) function c_get_default() bind(c, name="c_get_default")
      import c_int
    end function
    subroutine c_set_scalar(v) bind(c, name="c_set_scalar")
      import c_int
      integer(c_int), value :: v
    end subroutine
    integer(c_int) function c_get_scalar() bind(c, name="c_get_scalar")
      import c_int
    end function
    subroutine c_set_array(i, v) bind(c, name="c_set_array")
      import c_int
      integer(c_int), value :: i, v
    end subroutine
    integer(c_int) function c_get_array(i) bind(c, name="c_get_array")
      import c_int
      integer(c_int), value :: i
    end function
  end interface
end module attributes_bind_variable_mod
program attributes_bind_variable_interop
  use iso_c_binding, only: c_int
  use attributes_bind_variable_mod
  implicit none
  integer :: checks
  checks = 0
  call c_set_default(11_c_int)
  call expect_equal(int(default_label_value), 11, 'default-label C write')
  default_label_value = 13_c_int
  call expect_equal(int(c_get_default()), 13, 'default-label Fortran write')
  call c_set_scalar(17_c_int)
  call expect_equal(int(scalar_value), 17, 'explicit scalar C write')
  scalar_value = 19_c_int
  call expect_equal(int(c_get_scalar()), 19, 'explicit scalar Fortran write')
  call c_set_array(0_c_int, 23_c_int)
  call c_set_array(1_c_int, 29_c_int)
  call expect_equal(int(array_value(2)), 23, 'array element two C write')
  call expect_equal(int(array_value(3)), 29, 'array element three C write')
  array_value(2) = 31_c_int
  array_value(3) = 37_c_int
  call expect_equal(int(c_get_array(0_c_int)), 31, 'array element two Fortran write')
  call expect_equal(int(c_get_array(1_c_int)), 37, 'array element three Fortran write')
  call expect_equal(size(empty_array), 0, 'zero-size BIND array admission')
  call expect_equal(checks, 9, 'check total before completion')
  write(*,'(a)') 'ATTRIBUTES BIND VARIABLE INTEROP OK'
contains
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ATTR-BIND-VAR-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program attributes_bind_variable_interop
