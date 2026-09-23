! rule: R1122
! covers: nonlabel-do-without-loop-control
program do_construct_form_nonlabel_without_loop_control
  implicit none
  integer :: i, n, after_label_count
  integer :: trace(3)
  trace = -777
  n = 0
  after_label_count = 0
  do
    n = n + 1
    if (n > 3) then
      write(*,'(a)') 'DCF:too-many-iterations'
      error stop
    end if
    trace(n) = 20 + n
    if (n == 3) exit
  end do
  if (n /= 3) then
    write(*,'(a)') 'DCF:do_construct_form_nonlabel_without_loop_control:count'
    error stop
  end if
  if (any(trace /= [21, 22, 23])) then
    write(*,'(a)') 'DCF:do_construct_form_nonlabel_without_loop_control:trace'
    error stop
  end if
  if (after_label_count /= 0) then
    write(*,'(a)') 'DCF:do_construct_form_nonlabel_without_loop_control:after-label-sentinel'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM NONLABEL WITHOUT LOOP CONTROL OK'
end program do_construct_form_nonlabel_without_loop_control
