program block_save_local_persists
implicit none
integer :: pass, observed(3)
observed=-1
do pass=1,3
  block
    integer :: kept
    save :: kept
    if (pass == 1) kept=0
    kept=kept+1
    observed(pass)=kept
  end block
end do
if (any(observed /= [1,2,3])) error stop 1
write(*,'(a)') 'BLOCK SAVE LOCAL OK'
end program block_save_local_persists
