module save_result_control_mod
contains
  function unsaved_result() result(answer)
    implicit none
    integer :: answer
    answer = 7
  end function unsaved_result
end module save_result_control_mod
program save_result_control
  use save_result_control_mod
  implicit none
  if (unsaved_result() /= 7) error stop
  print '(a)', 'SAVE RESULT CONTROL OK'
end program save_result_control
