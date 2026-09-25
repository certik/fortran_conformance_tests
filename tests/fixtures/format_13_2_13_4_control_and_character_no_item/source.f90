! rule: S13.4-005
! covers: control-and-character-no-item
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_control_and_character_no_item
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks = 0
  buf = '###'
  write(buf,'("A",1X,"B")')
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:control_and_character_no_item:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= 'A B') then
    write(*,'(a)') 'F132134:control_and_character_no_item:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:control_and_character_no_item:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 CONTROL_AND_CHARACTER_NO_ITEM OK'
end program f132134_control_and_character_no_item
