! rule: S9.7.3.2-005
! covers: block-local-automatic-deallocation
! The first BLOCK execution proves allocation; the second execution observes unallocated status on entry.
program dealloc_block_local_auto
  implicit none
  integer :: pass, stat, checks
  checks = 0
  do pass = 1, 2
    block
      integer, allocatable :: local(:)
      if (allocated(local)) error stop 'D9732:block-local:entry-unallocated'
      checks = checks + 1
      if (pass == 1) then
        allocate(local(-6:-4), stat=stat)
        if (stat /= 0) error stop 'D9732:block-local:first-stat'
        local = [157, 163, 167]
        if (.not. allocated(local)) error stop 'D9732:block-local:first-allocated'
        checks = checks + 1
        if (lbound(local,1) /= -6) error stop 'D9732:block-local:first-lower'
        checks = checks + 1
        if (ubound(local,1) /= -4) error stop 'D9732:block-local:first-upper'
        checks = checks + 1
        if (any(local /= [157, 163, 167])) error stop 'D9732:block-local:first-values'
        checks = checks + 1
      else
        allocate(local(7:9), stat=stat)
        if (stat /= 0) error stop 'D9732:block-local:second-stat'
        local = [173, 179, 181]
        if (lbound(local,1) /= 7) error stop 'D9732:block-local:second-lower'
        checks = checks + 1
        if (ubound(local,1) /= 9) error stop 'D9732:block-local:second-upper'
        checks = checks + 1
        if (any(local /= [173, 179, 181])) error stop 'D9732:block-local:second-values'
        checks = checks + 1
      end if
    end block
  end do
  if (checks /= 9) error stop 'D9732:block-local:check-total'
  write(*,'(a)') 'DEALLOC BLOCK LOCAL AUTO OK'
end program dealloc_block_local_auto
