! rule: S16.9.3-003
! covers: achar-ascii-code-88-is-x
! covers: achar-ascii-digit-and-letter-codes
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_achar_ascii_mapping
  implicit none
  integer :: checks
  character(len=1) :: x, zero, upper, lower
  checks=0
  x = achar(88)
  zero = achar(48)
  upper = achar(65)
  lower = achar(122)
  if (.not. (len(x)==1 .and. len(zero)==1 .and. len(upper)==1 .and. len(lower)==1)) then
    write(*,'(a)') 'I16A:achar_ascii_mapping:lengths-one'
    error stop
  end if
  checks=checks+1
  if (x /= 'X') then
    write(*,'(a)') 'I16A:achar_ascii_mapping:code-88-x'
    error stop
  end if
  checks=checks+1
  if (zero /= '0') then
    write(*,'(a)') 'I16A:achar_ascii_mapping:digit-zero'
    error stop
  end if
  checks=checks+1
  if (upper /= 'A') then
    write(*,'(a)') 'I16A:achar_ascii_mapping:letter-a'
    error stop
  end if
  checks=checks+1
  if (lower /= 'z') then
    write(*,'(a)') 'I16A:achar_ascii_mapping:letter-z'
    error stop
  end if
  checks=checks+1
  if (checks /= 5) then
    write(*,'(a)') 'I16A:achar_ascii_mapping:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACHAR ASCII MAPPING OK'
end program intrinsics_16_9_a_achar_ascii_mapping
