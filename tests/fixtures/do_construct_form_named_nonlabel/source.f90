! rule: R1122
! covers: named-nonlabel-do-stmt
program do_construct_form_named_nonlabel
  implicit none
  integer :: i, n, after_label_count
  integer :: trace(3)
  trace = -777
  n = 0
  after_label_count = 0
  outer: do i = 1, 3
    n = n + 1
    if (n > 3) then
      write(*,'(a)') 'DCF:too-many-iterations'
      error stop
    end if
    trace(n) = 10 + i
  end do outer
  if (n /= 3) then
    write(*,'(a)') 'DCF:do_construct_form_named_nonlabel:count'
    error stop
  end if
  if (any(trace /= [11, 12, 13])) then
    write(*,'(a)') 'DCF:do_construct_form_named_nonlabel:trace'
    error stop
  end if
  if (after_label_count /= 0) then
    write(*,'(a)') 'DCF:do_construct_form_named_nonlabel:after-label-sentinel'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM NAMED NONLABEL OK'
end program do_construct_form_named_nonlabel
