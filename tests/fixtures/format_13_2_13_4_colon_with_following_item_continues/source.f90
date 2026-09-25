! rule: S13.4-007
! covers: colon-with-following-item-continues
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_colon_with_following_item_continues
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks = 0
  buf = '###'
  write(buf,'(SS,I1,:,",",I1)') 4,5
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:colon_with_following_item_continues:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '4,5') then
    write(*,'(a)') 'F132134:colon_with_following_item_continues:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:colon_with_following_item_continues:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 COLON_WITH_FOLLOWING_ITEM_CONTINUES OK'
end program f132134_colon_with_following_item_continues
