! rule: R1133
! covers: continue-stmt-alternative
program do_construct_form_continue_end
  implicit none
  integer :: i, n, after_label_count
  integer :: trace(3)
  trace = -777
  n = 0
  after_label_count = 0
  do 170 i = 1, 3
    n = n + 1
    if (n > 3) then
      write(*,'(a)') 'DCF:too-many-iterations'
      error stop
    end if
    trace(n) = 10 + i
  170 continue
  after_label_count = after_label_count + 1
  if (n /= 3) then
    write(*,'(a)') 'DCF:do_construct_form_continue_end:count'
    error stop
  end if
  if (any(trace /= [11, 12, 13])) then
    write(*,'(a)') 'DCF:do_construct_form_continue_end:trace'
    error stop
  end if
  if (after_label_count /= 1) then
    write(*,'(a)') 'DCF:do_construct_form_continue_end:after-label'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM CONTINUE END OK'
end program do_construct_form_continue_end
