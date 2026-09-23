! rule: S13.9-002
! covers: string-includes-blanks
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_string_descriptor_includes_blank
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks=0
  buf = repeat('#', len(buf))
  write(buf,'("A B")')
  if (len(buf) /= 3) then
    write(*,'(a)') 'CED:string_descriptor_includes_blank:observed-length'
    error stop
  end if
  checks=checks+1
  if (buf /= 'A B') then
    write(*,'(a)') 'CED:string_descriptor_includes_blank:observed-characters'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CED:string_descriptor_includes_blank:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT STRING_DESCRIPTOR_INCLUDES_BLANK OK'
end program ced_string_descriptor_includes_blank
