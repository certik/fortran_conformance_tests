module save_dummy_control_mod
contains
  subroutine takes_unsaved_dummy(x)
    implicit none
    integer, intent(in) :: x
    if (x /= 5) error stop
  end subroutine takes_unsaved_dummy
end module save_dummy_control_mod
program save_dummy_control
  use save_dummy_control_mod
  implicit none
  call takes_unsaved_dummy(5)
  print '(a)', 'SAVE DUMMY CONTROL OK'
end program save_dummy_control
