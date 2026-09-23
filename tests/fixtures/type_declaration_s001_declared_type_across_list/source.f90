program main
  implicit none
  interface which
    procedure which_integer
    procedure which_real
  end interface
  integer :: first = 11, second = 13
  if (which(first) /= 1) error stop
  if (which(second) /= 1) error stop
  if (first /= 11) error stop
  if (second /= 13) error stop
  print '(a)', 'type_declaration s001 list type ok'
contains
  integer function which_integer(value)
    integer, intent(in) :: value
    which_integer = 1
  end function which_integer
  integer function which_real(value)
    real, intent(in) :: value
    which_real = 2
  end function which_real
end program main
