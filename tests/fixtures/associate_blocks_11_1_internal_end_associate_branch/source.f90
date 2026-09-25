! rule: S11.1.3.2-005
! covers: internal-end-associate-branch-control
program ab1132_end_branch
  implicit none
  integer :: x, after
  x=1; after=-1
  associate (a => x)
    a=44
    goto 60
    a=-44
60 end associate
  after=x
  if (x /= 44) then
    write(*,'(a)') 'ENDX'
    error stop
  end if
  if (after /= 44) then
    write(*,'(a)') 'ENDAFTER'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS END BRANCH OK'

end program ab1132_end_branch
