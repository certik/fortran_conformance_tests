module interface_block_c1507_control_m
  implicit none
  interface g
    module procedure s
  end interface g
contains
  integer function s(i)
    integer, intent(in) :: i
    s = 42 + i
  end function s
end module interface_block_c1507_control_m
program interface_block_c1507_control
  use interface_block_c1507_control_m
  implicit none
  integer :: observed
  observed = -99
  observed = g(-5)
  if (observed /= 37) error stop 1
  print '(a)', 'INTERFACE BLOCK C1507 CONTROL OK'
end program interface_block_c1507_control
