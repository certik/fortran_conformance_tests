! rule: R1121
! covers: label-do-with-loop-control
program do_construct_form_label_with_loop_control
  implicit none
  integer :: i, n, after_label_count
  integer :: trace(3)
  trace = -777
  n = 0
  after_label_count = 0
  do 150 i = 1, 3
    n = n + 1
    if (n > 3) then
      write(*,'(a)') 'DCF:too-many-iterations'
      error stop
    end if
    trace(n) = 10 + i
  150 continue
  after_label_count = after_label_count + 1
  if (n /= 3) then
    write(*,'(a)') 'DCF:do_construct_form_label_with_loop_control:count'
    error stop
  end if
  if (any(trace /= [11, 12, 13])) then
    write(*,'(a)') 'DCF:do_construct_form_label_with_loop_control:trace'
    error stop
  end if
  if (after_label_count /= 1) then
    write(*,'(a)') 'DCF:do_construct_form_label_with_loop_control:after-label'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM LABEL WITH LOOP CONTROL OK'
end program do_construct_form_label_with_loop_control
