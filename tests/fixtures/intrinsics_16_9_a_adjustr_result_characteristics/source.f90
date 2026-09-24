! rule: S16.9.9-004
! covers: result-same-length
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_adjustr_result_characteristics
  implicit none
  integer :: checks
  character(len=5) :: s, r
  checks=0
  s = 'AB#  '
  r = adjustr(s)
  if (len(adjustr(s)) /= 5) then
    write(*,'(a)') 'I16A:adjustr_result_characteristics:same-length'
    error stop
  end if
  checks=checks+1
  if (r /= '  AB#') then
    write(*,'(a)') 'I16A:adjustr_result_characteristics:value-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'I16A:adjustr_result_characteristics:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ADJUSTR RESULT CHARACTERISTICS OK'
end program intrinsics_16_9_a_adjustr_result_characteristics
