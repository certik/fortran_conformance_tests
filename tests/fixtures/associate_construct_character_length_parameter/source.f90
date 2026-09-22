! rule: S11.1.3.2-003
! covers: character-length-type-parameter
! Oracle values are derived from Fortran 2023 11.1.3.2 or 11.1.3.3.
program associate_construct_character_length_parameter_effect
  implicit none
  integer :: checks
  character(len=9) :: parent
  parent='abcdefghi'
  checks=0
  ! The selector parent(3:8) has character length type parameter 6.
  associate (slice => parent(3:8))
  if (len(slice) /= 6) then
    write(*,'(a)') 'ACF:character_length_parameter:slice-length'
    error stop
  end if
  checks=checks+1
  if (len(parent) /= 9) then
    write(*,'(a)') 'ACF:character_length_parameter:parent-length-control'
    error stop
  end if
  checks=checks+1
  end associate
  if (checks /= 2) then
    write(*,'(a)') 'ACF:character_length_parameter:check-total'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE CHARACTER LENGTH PARAMETER OK'
end program associate_construct_character_length_parameter_effect
