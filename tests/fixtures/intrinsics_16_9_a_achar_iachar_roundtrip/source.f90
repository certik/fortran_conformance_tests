! rule: S16.9.3-005
! covers: achar-iachar-default-character-roundtrip
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_achar_iachar_roundtrip
  implicit none
  integer :: checks
  character(len=1) :: a, z, zero, under
  checks=0
  a = achar(iachar('A'))
  if (.not. (len(a) == 1 .and. a == 'A')) then
    write(*,'(a)') 'I16A:achar_iachar_roundtrip:roundtrip-a'
    error stop
  end if
  checks=checks+1
  z = achar(iachar('z'))
  if (.not. (len(z) == 1 .and. z == 'z')) then
    write(*,'(a)') 'I16A:achar_iachar_roundtrip:roundtrip-z'
    error stop
  end if
  checks=checks+1
  zero = achar(iachar('0'))
  if (.not. (len(zero) == 1 .and. zero == '0')) then
    write(*,'(a)') 'I16A:achar_iachar_roundtrip:roundtrip-zero'
    error stop
  end if
  checks=checks+1
  under = achar(iachar('_'))
  if (.not. (len(under) == 1 .and. under == '_')) then
    write(*,'(a)') 'I16A:achar_iachar_roundtrip:roundtrip-underscore'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'I16A:achar_iachar_roundtrip:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ACHAR IACHAR ROUNDTRIP OK'
end program intrinsics_16_9_a_achar_iachar_roundtrip
