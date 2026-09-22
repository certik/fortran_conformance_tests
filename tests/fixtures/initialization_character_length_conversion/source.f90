! rule: S8.4-001
! covers: character-length-conversion
! Distinctive nonzero/nonblank initialization sentinels are observed before executable overwrite.
program initialization_character_length_conversion_effect
  implicit none
  character(len=2) :: trunc = 'Zq7R'
  character(len=5) :: padded = 'Bx'
  integer :: checks
  checks=0
  if (len(trunc) /= 2) then
    write(*,'(a)') 'INIT:character_length_conversion:trunc-len'
    error stop
  end if
  checks=checks+1
  if (trunc(1:2) /= 'Zq') then
    write(*,'(a)') 'INIT:character_length_conversion:trunc-value'
    error stop
  end if
  checks=checks+1
  if (len(padded) /= 5) then
    write(*,'(a)') 'INIT:character_length_conversion:padded-len'
    error stop
  end if
  checks=checks+1
  if (padded(1:2) /= 'Bx') then
    write(*,'(a)') 'INIT:character_length_conversion:padded-prefix'
    error stop
  end if
  checks=checks+1
  if (padded(3:3) /= ' ') then
    write(*,'(a)') 'INIT:character_length_conversion:padded-tail-blank-1'
    error stop
  end if
  checks=checks+1
  if (padded(4:4) /= ' ') then
    write(*,'(a)') 'INIT:character_length_conversion:padded-tail-blank-2'
    error stop
  end if
  checks=checks+1
  if (padded(5:5) /= ' ') then
    write(*,'(a)') 'INIT:character_length_conversion:padded-tail-blank-3'
    error stop
  end if
  checks=checks+1
  if (checks /= 7) then
    write(*,'(a)') 'INIT:character_length_conversion:check-total'
    error stop
  end if
  write(*,'(a)') 'INITIALIZATION CHARACTER LENGTH CONVERSION OK'
end program initialization_character_length_conversion_effect
