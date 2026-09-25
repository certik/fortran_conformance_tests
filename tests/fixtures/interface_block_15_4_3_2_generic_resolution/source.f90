module interface_block_generic_resolution_m
  implicit none
  ! rule: S15.4.3.2-002 S15.4.3.2-004
  ! covers: generic interface block with MODULE PROCEDURE specifics
  interface choose
    module procedure choose_int, choose_log
  end interface choose
contains
  integer function choose_int(i)
    integer, intent(in) :: i
    choose_int = 42 + i
  end function choose_int
  logical function choose_log(flag)
    logical, intent(in) :: flag
    choose_log = .not. flag
  end function choose_log
  integer function wrong_int(i)
    integer, intent(in) :: i
    wrong_int = 41 + i
  end function wrong_int
  logical function wrong_log(flag)
    logical, intent(in) :: flag
    wrong_log = flag
  end function wrong_log
end module interface_block_generic_resolution_m

program interface_block_generic_resolution
  use interface_block_generic_resolution_m
  implicit none
  integer :: ivalue
  logical :: lvalue
  ivalue = -100
  ivalue = choose(-5)
  if (ivalue /= 37) error stop 1
  lvalue = .true.
  lvalue = choose(.true.)
  if (lvalue .neqv. .false.) error stop 2
  print '(a)', 'INTERFACE BLOCK GENERIC RESOLUTION OK'
end program interface_block_generic_resolution
