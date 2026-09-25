module interface_block_c1509_control_m
  implicit none
  interface g
    module procedure s
  end interface
  interface g
    module procedure s
  end interface
contains
  integer function s(i)
    integer, intent(in) :: i
    s = 42 + i
  end function s
  logical function t(flag)
    logical, intent(in) :: flag
    t = .not. flag
  end function t
end module interface_block_c1509_control_m
program interface_block_c1509_control
  use interface_block_c1509_control_m
  implicit none
  if (g(-5) /= 37) error stop 1
  if (g(.true.) .neqv. .false.) error stop 2
  print '(a)', 'INTERFACE BLOCK C1509 CONTROL OK'
end program interface_block_c1509_control
