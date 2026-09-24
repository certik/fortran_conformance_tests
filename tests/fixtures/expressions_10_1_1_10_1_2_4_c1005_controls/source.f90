module expr_c1005_long_m
  implicit none
  interface operator(.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.)
    module procedure longop_impl
  end interface
contains
  integer function longop_impl(x)
    integer, intent(in) :: x
    longop_impl = 1000 + x
  end function longop_impl
end module expr_c1005_long_m
program expr_c1005_controls
  use expr_c1005_long_m
  implicit none
  integer :: checks, x
  checks=0
  x = .aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa. 7
  if (x /= 1007) error stop 'EC1005:long'
  checks=checks+1
  if (checks /= 1) error stop 'EC1005:checks'
  write(*,'(a)') 'EXPRESSIONS C1005 CONTROLS OK'
end program expr_c1005_controls
