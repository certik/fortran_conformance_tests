! rule: S13.4-006
! covers: data-descriptor-without-item-terminates
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_data_descriptor_without_item_terminates
  implicit none
  integer :: checks
  character(len=2) :: buf
  checks = 0
  buf = '##'
  write(buf,'(SS,I1,I1)') 4
  if (len(buf) /= 2) then
    write(*,'(a)') 'F132134:data_descriptor_without_item_terminates:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '4 ') then
    write(*,'(a)') 'F132134:data_descriptor_without_item_terminates:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:data_descriptor_without_item_terminates:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 DATA_DESCRIPTOR_WITHOUT_ITEM_TERMINATES OK'
end program f132134_data_descriptor_without_item_terminates
