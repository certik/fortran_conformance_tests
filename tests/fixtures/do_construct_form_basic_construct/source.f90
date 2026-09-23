! rule: R1119
! covers: do-construct-form
program do_construct_form_basic_construct
  implicit none
  integer :: i, n, after_label_count
  integer :: trace(3)
  trace = -777
  n = 0
  after_label_count = 0
  do i = 1, 3
    n = n + 1
    if (n > 3) then
      write(*,'(a)') 'DCF:too-many-iterations'
      error stop
    end if
    trace(n) = 10 + i
  end do
  if (n /= 3) then
    write(*,'(a)') 'DCF:do_construct_form_basic_construct:count'
    error stop
  end if
  if (any(trace /= [11, 12, 13])) then
    write(*,'(a)') 'DCF:do_construct_form_basic_construct:trace'
    error stop
  end if
  if (after_label_count /= 0) then
    write(*,'(a)') 'DCF:do_construct_form_basic_construct:after-label-sentinel'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM BASIC CONSTRUCT OK'
end program do_construct_form_basic_construct
