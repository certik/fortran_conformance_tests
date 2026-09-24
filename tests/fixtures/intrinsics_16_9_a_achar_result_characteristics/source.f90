! rule: S16.9.3-002
! covers: achar-result-length-one
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_achar_result_characteristics
  implicit none
  integer :: checks
  character(len=1) :: c
  checks=0
  c = achar(88)
  if (len(achar(88)) /= 1) then
    write(*,'(a)') 'I16A:achar_result_characteristics:length-one'
    error stop
  end if
  checks=checks+1
  if (c /= 'X') then
    write(*,'(a)') 'I16A:achar_result_characteristics:value-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'I16A:achar_result_characteristics:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACHAR RESULT CHARACTERISTICS OK'
end program intrinsics_16_9_a_achar_result_characteristics
