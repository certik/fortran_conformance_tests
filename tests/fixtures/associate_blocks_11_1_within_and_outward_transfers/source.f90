! rule: S11.1.2.1-002
! covers: within-block-transfer-source, out-of-block-transfer-source
program ab1121_transfers
  implicit none
  integer :: within_value, outward_value, after_value
  within_value=-1; outward_value=-2; after_value=-3
  block
    goto 10
    within_value=-10
10  within_value=31
  end block
  block
    outward_value=43
    goto 30
    outward_value=-43
  end block
  outward_value=-99
30 after_value=57
  if (within_value /= 31) then
    write(*,'(a)') 'WITHIN'
    error stop
  end if
  if (outward_value /= 43) then
    write(*,'(a)') 'OUTWARD'
    error stop
  end if
  if (after_value /= 57) then
    write(*,'(a)') 'AFTER'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS TRANSFERS OK'

end program ab1121_transfers
