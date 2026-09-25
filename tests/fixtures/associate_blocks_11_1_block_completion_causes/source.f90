! rule: S11.1.2.2-002
! covers: last-construct-completion, ...
program ab1122_completion
  implicit none
  integer :: last_value, branch_value, return_value, exit_value, cycle_value, i
  last_value=-1; branch_value=-2; return_value=-3; exit_value=-4; cycle_value=0
  block
    last_value=201
  end block
  block
    branch_value=202
    goto 40
    branch_value=-202
  end block
  branch_value=-99
40 continue
  call returner(return_value)
  do i=1,4
    block
      if (i == 2) cycle
      if (i == 4) exit
      cycle_value=cycle_value+i
    end block
    exit_value=i
  end do
  if (last_value /= 201) then
    write(*,'(a)') 'LAST'
    error stop
  end if
  if (branch_value /= 202) then
    write(*,'(a)') 'BRANCH'
    error stop
  end if
  if (return_value /= 203) then
    write(*,'(a)') 'RETURN'
    error stop
  end if
  if (cycle_value /= 4) then
    write(*,'(a)') 'CYCLE'
    error stop
  end if
  if (exit_value /= 3) then
    write(*,'(a)') 'EXIT'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS COMPLETION OK'

contains
  subroutine returner(v)
    integer, intent(out) :: v
    block
      v=203
      return
    end block
    v=-203
  end subroutine returner
end program ab1122_completion
