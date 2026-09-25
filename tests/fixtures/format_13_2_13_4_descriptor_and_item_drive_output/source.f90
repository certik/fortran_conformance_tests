! rule: S13.4-001
! covers: descriptor-and-item-drive-output
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_descriptor_and_item_drive_output
  implicit none
  integer :: checks
  character(len=2) :: buf
  checks = 0
  buf = '##'
  write(buf,'(SS,I2)') 9
  if (len(buf) /= 2) then
    write(*,'(a)') 'F132134:descriptor_and_item_drive_output:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= ' 9') then
    write(*,'(a)') 'F132134:descriptor_and_item_drive_output:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:descriptor_and_item_drive_output:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 DESCRIPTOR_AND_ITEM_DRIVE_OUTPUT OK'
end program f132134_descriptor_and_item_drive_output
