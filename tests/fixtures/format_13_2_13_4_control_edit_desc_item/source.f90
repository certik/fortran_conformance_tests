! rule: R1304
! covers: control-edit-desc-item
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_control_edit_desc_item
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks = 0
  buf = '###'
  write(buf,'(SS,1X,I1)') 7
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:control_edit_desc_item:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= ' 7 ') then
    write(*,'(a)') 'F132134:control_edit_desc_item:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:control_edit_desc_item:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 CONTROL_EDIT_DESC_ITEM OK'
end program f132134_control_edit_desc_item
