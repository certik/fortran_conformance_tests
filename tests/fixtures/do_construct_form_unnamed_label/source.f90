! rule: R1121
! covers: unnamed-label-do-stmt
program do_construct_form_unnamed_label
  implicit none
  integer :: i, n, after_label_count
  integer :: trace(3)
  trace = -777
  n = 0
  after_label_count = 0
  do 130 i = 1, 3
    n = n + 1
    if (n > 3) then
      write(*,'(a)') 'DCF:too-many-iterations'
      error stop
    end if
    trace(n) = 10 + i
  130 continue
  after_label_count = after_label_count + 1
  if (n /= 3) then
    write(*,'(a)') 'DCF:do_construct_form_unnamed_label:count'
    error stop
  end if
  if (any(trace /= [11, 12, 13])) then
    write(*,'(a)') 'DCF:do_construct_form_unnamed_label:trace'
    error stop
  end if
  if (after_label_count /= 1) then
    write(*,'(a)') 'DCF:do_construct_form_unnamed_label:after-label'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM UNNAMED LABEL OK'
end program do_construct_form_unnamed_label
