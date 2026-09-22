! rule: S8.4-005
! covers: block-retention
! Distinctive nonzero/nonblank initialization sentinels are observed before executable overwrite.
program initialization_block_retention_effect
  implicit none
  integer :: pass, first, second, checks
  checks=0
  first=-9
  second=-9
  do pass=1,2
    block
      integer :: kept = -27182
      if (pass == 1) then
        first = kept
        kept = -27181
      else
        second = kept
        kept = -27180
      end if
    end block
  end do
  if (first /= -27182) then
    write(*,'(a)') 'INIT:block_retention:first-block-execution'
    error stop
  end if
  checks=checks+1
  if (second /= -27181) then
    write(*,'(a)') 'INIT:block_retention:second-block-execution'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'INIT:block_retention:check-total'
    error stop
  end if
  write(*,'(a)') 'INITIALIZATION BLOCK RETENTION OK'
end program initialization_block_retention_effect
