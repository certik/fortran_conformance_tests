! rule: R1125
! covers: concurrent-header-without-type-spec
program do_construct_form_concurrent_header_without_type
  implicit none
  integer :: trace(4)
  integer :: i
  trace = -777
  do concurrent (i = 1:4)
    trace(i) = 10 + i
  end do
  if (any(trace /= [11, 12, 13, 14])) then
    write(*,'(a)') 'DCF:do_construct_form_concurrent_header_without_type:trace'
    error stop
  end if
  if (count(trace /= -777) /= 4) then
    write(*,'(a)') 'DCF:do_construct_form_concurrent_header_without_type:count'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM CONCURRENT HEADER WITHOUT TYPE OK'
end program do_construct_form_concurrent_header_without_type
