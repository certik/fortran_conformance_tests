! rule: S13.4-008
! covers: unlimited-item-reuses-list
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_unlimited_item_reuses_list
  implicit none
  integer :: checks
  character(len=5) :: buf
  checks = 0
  buf = '#####'
  write(buf,'(SS,*(I1,:,";"))') 1,2,3
  if (len(buf) /= 5) then
    write(*,'(a)') 'F132134:unlimited_item_reuses_list:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '1;2;3') then
    write(*,'(a)') 'F132134:unlimited_item_reuses_list:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:unlimited_item_reuses_list:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 UNLIMITED_ITEM_REUSES_LIST OK'
end program f132134_unlimited_item_reuses_list
