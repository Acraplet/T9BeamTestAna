const int nChannels = 8;
struct MidasEvent{
    int midasEvent;
    int timestamp;
    int freqsetting;
    uint64_t triggerTime;
    TH1D* waveforms[nChannels];
    
    void Initialize(){
        midasEvent = 0;
        timestamp = 0;
        freqsetting = 0;
        triggerTime = 0;
        for(int i = 0; i < nChannels; i++) waveforms[i] = NULL;
    }
};

void PrintSpills(vector<vector<uint64_t>> v1, vector<vector<uint64_t>> v2){
    int sz1 = v1.size();
    int sz2 = v2.size();
        
    int total = (sz1 >= sz2) ? sz1 : sz2;  
    cout << "++++++++++++++++++++++++++++++++++++++++++++" << endl;
    for(int i = 0; i < total; i++){
        int n1 = (i < sz1) ? v1.at(i).size() : 0;
        int n2 = (i < sz2) ? v2.at(i).size() : 0;
        cout << i;
        if(n1 > n2) cout << " ----> ";
        else cout << "       ";
         
        cout  << n1 << "    " << n2;
        
        if(n1 < n2) cout << " <---- " << endl;
        else cout << endl;
    } 
} 

void PrintSpill(vector<uint64_t> v1, vector<uint64_t> v2){
    int sz1 = v1.size();
    int sz2 = v2.size();
    int total = (sz1 >= sz2) ? sz1 : sz2;  
    cout << "++++++++++++++++++++++++++++++++++++++++++++" << endl;
    for(int i = 0; i < total; i++){
        uint64_t n1 = (i < sz1) ? v1.at(i) : 0;
        uint64_t n2 = (i < sz2) ? v2.at(i) : 0;
        uint64_t diff = n1>n2 ? n1-n2 : n2-n1;
        cout << i << " " << n1 << "    " << n2 << "    " << diff << endl;
    } 
}
void EventMatching(string fileName){
    
    
    MidasEvent event1;
    event1.Initialize();
    
    MidasEvent event2;
    event2.Initialize();
    
    TFile inFile(fileName.c_str(), "READ");
    
    
    TTree *tree1 = (TTree*) inFile.Get("midas_data1");

    tree1->SetBranchAddress("midasEvent",&event1.midasEvent);
    tree1->SetBranchAddress("timestamp",&event1.timestamp);
    tree1->SetBranchAddress("freqsetting",&event1.freqsetting);
    tree1->SetBranchAddress("triggerTime",&event1.triggerTime);
    for(int i = 0; i < nChannels; i++){
        tree1->SetBranchAddress(Form("Channel%d",i),&(event1.waveforms[i]));
    }

    TTree *tree2 = (TTree*) inFile.Get("midas_data2");

    tree2->SetBranchAddress("midasEvent",&event2.midasEvent);
    tree2->SetBranchAddress("timestamp",&event2.timestamp);
    tree2->SetBranchAddress("freqsetting",&event2.freqsetting);
    tree2->SetBranchAddress("triggerTime",&event2.triggerTime);
    for(int i = 0; i < nChannels; i++){
        tree2->SetBranchAddress(Form("Channel%d",i),&(event2.waveforms[i]));
    }
    
    int ent1 = tree1->GetEntries();
    int ent2 = tree1->GetEntries();
    
    vector<vector<uint64_t>> spills1;
    vector<vector<uint64_t>> spills2;
    
    vector<uint64_t> temp;
    cout << "****************************************Processing MIDAS data 1****************************************" << endl;
    for(int i = 0; i < ent1; i++){
        tree1->GetEntry(i);
        if(!((i+1)%10000)) cout << "    Processing event: " << i+1 << endl;
        
        if(i == 0){
            temp.push_back(event1.triggerTime);
            continue;
        }
        
        uint64_t diff = max(event1.triggerTime, temp.at(temp.size()-1)) - min(event1.triggerTime, temp.at(temp.size()-1));
        if(diff>5e9){
           spills1.push_back(temp);
           temp.clear();
           temp.push_back(event1.triggerTime);
        }
        else{
            temp.push_back(event1.triggerTime);
        }
    } 
    spills1.push_back(temp);
    temp.clear();
    
    cout << "****************************************Processing MIDAS data 2****************************************" << endl;
    for(int i = 0; i < ent2; i++){
        tree2->GetEntry(i);
        if(!((i+1)%10000)) cout << "    Processing event: " << i+1 << endl;
        
        if(i == 0){
            temp.push_back(event2.triggerTime);
            continue;
        }
        
        uint64_t diff = max(event2.triggerTime, temp.at(temp.size()-1)) - min(event2.triggerTime, temp.at(temp.size()-1));
        if(diff>5e9){
           spills2.push_back(temp);
           temp.clear();
           temp.push_back(event2.triggerTime);
        }
        else{
            temp.push_back(event2.triggerTime);
        }
    } 
    spills2.push_back(temp);
    temp.clear();  
    
    cout << "********************************************Spill analysis********************************************" << endl;
    
    cout << "Found spills (midas1, midas2) = " << spills1.size() << " " << spills2.size() << endl;
    
    /*if(spills1.size() != spills2.size()){
        cout << "Mismatch between number of spills!" << endl;
        return;
    }*/
    
    //int total = 0;
    PrintSpills(spills1, spills2);

    
    
    int sz1 = spills1.size();
    int sz2 = spills2.size();
    
    
    vector<vector<uint64_t>> nspills1;
    vector<vector<uint64_t>> nspills2;
    
    
        
    int total = (sz1 >= sz2) ? sz1 : sz2;
    
    int counter1 = 0;
    int counter2 = 0;
    while(counter1 < sz1 || counter2 < sz2){
        
        //cout << counter1 << " " << counter2 << endl;
        if(counter1 < sz1 && counter2 >= sz2){
            nspills1.push_back(spills1.at(counter1));
            counter1++;
            continue;
        }
        else if(counter1 >= sz1 && counter2 < sz2){
            nspills2.push_back(spills2.at(counter2));
            counter2++;
            continue;
        }

        int n1 = spills1.at(counter1).size();
        int n2 = spills2.at(counter2).size();
        
        if(n1 == n2 && n1>10 && n2>10){
            nspills1.push_back(spills1.at(counter1));
            nspills2.push_back(spills2.at(counter2));
            
            counter1++;
            counter2++;
            continue;
        }

        if(n1 < 10 && n2 < 10 && counter1 < sz1-1 && counter2 < sz2-1){
            int n3 = spills1.at(counter1+1).size();
            int n4 = spills2.at(counter2+1).size();
            
            if((n1+n3 > 10 && n2+n4 > 10)){
                if(abs(n1+n3-n2-n4) < 10){
                    vector<uint64_t> temp1;
                    vector<uint64_t> temp2;
                    temp1.insert(temp1.end(), spills1.at(counter1).begin(), spills1.at(counter1).end());
                    temp1.insert(temp1.end(), spills1.at(counter1+1).begin(), spills1.at(counter1+1).end());

                    temp2.insert(temp2.end(), spills2.at(counter2).begin(), spills2.at(counter2).end());
                    temp2.insert(temp2.end(), spills2.at(counter2+1).begin(), spills2.at(counter2+1).end());
                    
                    nspills1.push_back(temp1);              
                    nspills2.push_back(temp2);
                    
                    
                    counter1 +=2;
                    counter2 +=2;
                    continue;
                } 
            } 
         
            else{
                int n5 = spills1.at(counter1+2).size();
                int n6 = spills2.at(counter2+2).size();
            
                if(abs(n1+n3+n5-n2-n4-n6) < 10){
                    vector<uint64_t> temp1;
                    vector<uint64_t> temp2;
                    temp1.insert(temp1.end(), spills1.at(counter1).begin(), spills1.at(counter1).end());
                    temp1.insert(temp1.end(), spills1.at(counter1+1).begin(), spills1.at(counter1+1).end());
                    temp1.insert(temp1.end(), spills1.at(counter1+2).begin(), spills1.at(counter1+2).end());

                    temp2.insert(temp2.end(), spills2.at(counter2).begin(), spills2.at(counter2).end());
                    temp2.insert(temp2.end(), spills2.at(counter2+1).begin(), spills2.at(counter2+1).end());
                    temp2.insert(temp2.end(), spills2.at(counter2+2).begin(), spills2.at(counter2+2).end());
                    
                    nspills1.push_back(temp1);              
                    nspills2.push_back(temp2);
                    
                    
                    counter1 +=3;
                    counter2 +=3;
                    continue;            
                }  
            }       
        }       
        if(counter1 < sz1-1){
            int n3 = spills1.at(counter1+1).size();
            
            if(abs(n1+n3-n2) < 10 && n1+n3 > 10){
                vector<uint64_t> temp1;
                temp1.insert(temp1.end(), spills1.at(counter1).begin(), spills1.at(counter1).end());
                temp1.insert(temp1.end(), spills1.at(counter1+1).begin(), spills1.at(counter1+1).end());
                
                nspills1.push_back(temp1);
                
                nspills2.push_back(spills2.at(counter2));
                
                counter1 +=2;
                counter2++ ;
                continue;
            }
        }             
        if(counter2 < sz2-1){
            int n3 = spills2.at(counter2+1).size();
            
            if(abs(n2+n3-n1) < 10 &&  n2+n3 > 10){
                vector<uint64_t> temp1;
                temp1.insert(temp1.end(), spills2.at(counter2).begin(), spills2.at(counter2).end());
                temp1.insert(temp1.end(), spills2.at(counter2+1).begin(), spills2.at(counter2+1).end());
                
                nspills2.push_back(temp1);
                
                nspills1.push_back(spills1.at(counter1));
                
                counter1++;
                counter2 +=2;
                continue;
            }
        }

        
        if(n1 < 10){
            nspills1.at(nspills1.size()-1).insert(nspills1.at(nspills1.size()-1).end(), spills1.at(counter1).begin(), spills1.at(counter1).end());
        }
        else{
            nspills1.push_back(spills1.at(counter1));
        }
        
        if(n2 < 10){
            nspills2.at(nspills2.size()-1).insert(nspills2.at(nspills2.size()-1).end(), spills2.at(counter2).begin(), spills2.at(counter2).end());
        }
        else{
            nspills2.push_back(spills2.at(counter2));
        }
        
        
        
        counter1++;
        counter2++;
                

    }
    
    cout << "********************************************Fixing spills********************************************" << endl;
    cout << "Found spills (midas1, midas2) = " << nspills1.size() << " " << nspills2.size() << endl;
    
    PrintSpills(nspills1, nspills2);
    
    //PrintSpill(nspills1.at(53), nspills2.at(53));
    
    vector<TH1D> hTiming1;
    vector<TH1D> hTiming2;
    vector<TH1D> hTiming3;
    vector<TCanvas> hTiming;
 
    string baseName =  fileName.substr(0, fileName.size()-5);
    string outName1 = baseName + "_timingPlots.root";
    TFile outFile(outName1.c_str(), "RECREATE");
    outFile.cd();   
    for(int i = 0; i < nspills1.size(); i++){
        string name1 = "hSpill" + to_string(i) + "_dig1";
        string name2 = "hSpill" + to_string(i) + "_dig2";
        string name3 = "hSpill" + to_string(i) + "_diff";
        
        int n = nspills1.at(i).size() > nspills2.at(i).size() ? 11*nspills1.at(i).size() : 11*nspills2.at(i).size();
        double min = 0;
        double max = nspills1.at(i).back()-nspills1.at(i).at(0) > nspills2.at(i).back() - nspills2.at(i).at(0) ? nspills1.at(i).back()-nspills1.at(i).at(0) : nspills2.at(i).back() - nspills2.at(i).at(0);
        max*=1.1;
        TH1D hTemp1(name1.c_str(), "Digitizer 1; Trigger time; Events", n, min, max);
        TH1D hTemp2(name2.c_str(), "Digitizer 2; Trigger time; Events", n, min, max);
        TH1D hTemp3(name3.c_str(), "Digitizer 1-Digitizer2; Trigger time; Events", n, min, max);
        hTemp1.SetStats(kFALSE);
        hTemp2.SetStats(kFALSE);
        hTemp3.SetStats(kFALSE);
        
        

        for(int j = 0; j < nspills1.at(i).size(); j++){
            hTemp1.Fill(nspills1.at(i).at(j) - nspills1.at(i).at(0));
        }
        for(int j = 0; j < nspills2.at(i).size(); j++){
            hTemp2.Fill(nspills2.at(i).at(j) - nspills2.at(i).at(0));
        }

        for(int i = 0; i < n; i++){
            hTemp3.SetBinContent(i+1, hTemp1.GetBinContent(i+1)-hTemp2.GetBinContent(i+1));
        }
        
        hTiming1.push_back(hTemp1);
        hTiming2.push_back(hTemp2);
        hTiming3.push_back(hTemp3);
        string name4 = "cSpill" + to_string(i);
        TCanvas c(name4.c_str(), "", 1600, 900);
        c.Divide(1,3);
        c.cd(1)->SetMargin(0.1, 0.1, 0.1, 0.1);
        c.cd(1)->SetTickx(kTRUE);
        c.cd(1)->SetTicks(kTRUE);
        hTiming1.back().Draw("HIST");
        c.cd(2)->SetMargin(0.1, 0.1, 0.1, 0.1);
        c.cd(2)->SetTicks(kTRUE);
        c.cd(2)->SetTicks(kTRUE);
        hTiming2.back().Draw("HIST");
        c.cd(3)->SetMargin(0.1, 0.1, 0.1, 0.1);
        c.cd(3)->SetTicks(kTRUE);
        c.cd(3)->SetTicks(kTRUE);
        hTiming3.back().SetMinimum(-1);
        hTiming3.back().SetMaximum(1);
        hTiming3.back().Draw("HIST");
        //hTiming.push_back(c);
        c.Write();
        
        
    }
    
    outFile.Close();
    /*or(int i = 0; i < nspills1.size(); i++){
        hTiming1.at(i).Write();
        hTiming2.at(i).Write();
    }*/
    
    
    cout << "********************************************Removing bad triggers********************************************" << endl;
    
    
    vector<vector<int>> save1;
    vector<vector<int>> save2; 
    
    for(int i = 0; i < nspills1.size(); i++){
        vector<int> temp1(nspills1.at(i).size(), 0);
        vector<int> temp2(nspills2.at(i).size(), 0);
        
        save1.push_back(temp1);
        save2.push_back(temp2);
    }
    
    double delta = 2.9e6;
    for(int i = 0; i < nspills1.size(); i++){
        for(int j = 0; j < nspills1.at(i).size(); j++){
        
            int ind2 = -1;
            bool pass = false;
            for(int k = 0; k < nspills2.at(i).size(); k++){
                uint64_t diff = nspills1.at(i).at(j) > nspills2.at(i).at(k) ? nspills1.at(i).at(j) - nspills2.at(i).at(k) : nspills2.at(i).at(k) - nspills1.at(i).at(j);
                
                if(diff < delta){
                    ind2 = k;
                    pass = true;
                    break;
                }
            }
            
            if(pass){
                save1.at(i).at(j) = 1;
                save2.at(i).at(ind2) = 1;
            }        
        }
    }
    
    string outName2 = baseName + "_clean.root";
    TFile outFileData(outName2.c_str(), "RECREATE");
    outFileData.cd();
    
    TTree* tree3 = new TTree("midas_data1","First Digitizer");

    tree3->Branch("midasEvent",&event1.midasEvent,"midasEvent/I");
    tree3->Branch("timestamp",&event1.timestamp,"timestamp/I");
    //tree3->Branch("serialnumber",&event1.serialnumber,"serialnumber/I");
    tree3->Branch("freqsetting",&event1.freqsetting,"freqsetting/I");
    tree3->Branch("triggerTime",&event1.triggerTime,"triggerTime/g");
    for(int i=0; i<8; i++) tree3->Branch(Form("Channel%d",i),"TH1D",&(event1.waveforms[i]));

    TTree* tree4 = new TTree("midas_data2","Second Digitizer");

    tree4->Branch("midasEvent",&event2.midasEvent,"midasEvent/I");
    tree4->Branch("timestamp",&event2.timestamp,"timestamp/I");
    //tree4->Branch("serialnumber",&serialnumber,"serialnumber/I");
    tree4->Branch("freqsetting",&event2.freqsetting,"freqsetting/I");
    tree4->Branch("triggerTime",&event2.triggerTime,"triggerTime/g");
    for(int i=0; i<8; i++) tree4->Branch(Form("Channel%d",i),"TH1D",&(event2.waveforms[i]));   
    

    cout << "****************************************Saving MIDAS data 1****************************************" << endl;
    
    int counter = -1;
    for(int i = 0; i < nspills1.size(); i++){
        for(int j = 0; j < nspills1.at(i).size(); j++){
            counter ++;
            if(!((counter+1)%10000)) cout << "    Processing event: " << counter+1 << endl;
            if(save1.at(i).at(j) == 0) continue;
            tree1->GetEntry(counter);
            tree3->Fill();
        }
    }

    cout << "****************************************Saving MIDAS data 2****************************************" << endl;
    counter = -1;
    for(int i = 0; i < nspills2.size(); i++){
        for(int j = 0; j < nspills2.at(i).size(); j++){
            counter ++;
            if(!((counter+1)%10000)) cout << "    Processing event: " << counter+1 << endl;
            if(save2.at(i).at(j) == 0) continue;
            tree2->GetEntry(counter);
            tree4->Fill();
        }
    }
    tree3->Write();
    tree4->Write();
    
    outFileData.Close();    
    /*vector<int> remove1;
    vector<int> remove2;
    
    int ind1 = 0;
    int ind2 = 0; 
    
    
    
    
    for(int i = 0; i < nspills1.size(); i++){
        //double delta = hTiming1.at(i).GetBinWidth(1) > hTiming2.at(i).GetBinWidth(1) ? hTiming2.at(i).GetBinWidth(1)/5 : hTiming1.at(i).GetBinWidth(1);
        //double delta = 2.9e6;
        double delta = hTiming1.at(i).GetBinWidth(1);
        //cout << delta << endl;

        //cout << sz1 << " " << sz2 << endl;
        
        int nRem1 = 0;
        int nRem2 = 0; 
        
        uint64_t diff0 =  nspills1.at(i).at(0) > nspills2.at(i).at(0) ? nspills1.at(i).at(0) - nspills2.at(i).at(0) : nspills2.at(i).at(0) - nspills1.at(i).at(0);

        if(diff0 > delta){

            uint64_t diff01 = nspills1.at(i).at(0) > nspills2.at(i).at(1) ? nspills1.at(i).at(0) - nspills2.at(i).at(1) : nspills2.at(i).at(1) - nspills1.at(i).at(0);
            uint64_t diff02 = nspills1.at(i).at(1) > nspills2.at(i).at(0) ? nspills1.at(i).at(1) - nspills2.at(i).at(0) : nspills2.at(i).at(0) - nspills1.at(i).at(1);
            if(diff01 < delta){
                remove2.push_back(ind2);  
                cout << "Removing trigger (2, " << i << ", 0)" << endl;
                nRem2++;
            }
            else if(diff02 < delta){
                remove1.push_back(ind1);
                cout << "Removing trigger (1, " << i << ", 0)" << endl;
                nRem1++;
            }
        }
        
        int ntrig = nspills1.at(i).size() > nspills2.at(i).size() ? nspills1.at(i).size() : nspills2.at(i).size();
        
        int sz1 = nspills1.at(i).size();
        int sz2 = nspills2.at(i).size();
        
        for(int j = 1; j<ntrig; j++){

            
            if(j >= sz1 && sz2-nRem2 > sz1){

                cout << "Removing trigger (2, " << i << ", " << j << ") --> size difference" << endl;
                remove2.push_back(ind2+j);

                nRem2++;

                continue;
            }
            else if(j >= sz2 && sz1-nRem1 > sz2){

                cout << "Removing trigger (1, " << i << ", " << j << ") --> size difference" <<  endl;
                remove1.push_back(ind1+j);

                nRem1++;

                continue;
            }
            
            
            if(j >= sz1) continue;
            if(j >= sz2) continue;
            
            uint64_t diff1 = nspills1.at(i).at(j+nRem1) - nspills1.at(i).at(j+nRem1-1);
            uint64_t diff2 = nspills2.at(i).at(j+nRem2) - nspills2.at(i).at(j+nRem2-1);

            if(diff1 > diff2){
                uint64_t diff = diff1-diff2;
                if(diff> delta){
                    cout << "Removing trigger (2, " << i << ", " << j << ", " << diff2 << ", " << delta <<")" <<  endl;
                    remove2.push_back(ind2+j+nRem2);

                    nRem2++;
                    continue;
                }
            }
            else if(diff1 < diff2){
                uint64_t diff = diff2-diff1;
                if(diff> delta){

                    cout << "Removing trigger (1, " << i << ", " << j << ", " << diff1 << ", " << delta <<")" <<  endl;
                    cout << nRem1 << " " << nRem2 << " " <<   nspills1.at(i).at(j+nRem1) << " " <<  nspills2.at(i).at(j+nRem2) << endl;
                    remove1.push_back(ind1+j+nRem1);
                    nRem1++;
                    continue;
                }                
            }

            
        }
        
        ind1 += sz1;
        ind2 += sz2;
    }
    
    string outName2 = baseName + "_clean.root";
    TFile outFileData(outName2.c_str(), "RECREATE");
    outFileData.cd();
    
    TTree* tree3 = new TTree("midas_data1","First Digitizer");

    tree3->Branch("midasEvent",&event1.midasEvent,"midasEvent/I");
    tree3->Branch("timestamp",&event1.timestamp,"timestamp/I");
    //tree3->Branch("serialnumber",&event1.serialnumber,"serialnumber/I");
    tree3->Branch("freqsetting",&event1.freqsetting,"freqsetting/I");
    tree3->Branch("triggerTime",&event1.triggerTime,"triggerTime/g");
    for(int i=0; i<8; i++) tree3->Branch(Form("Channel%d",i),"TH1D",&(event1.waveforms[i]));

    TTree* tree4 = new TTree("midas_data2","Second Digitizer");

    tree4->Branch("midasEvent",&event2.midasEvent,"midasEvent/I");
    tree4->Branch("timestamp",&event2.timestamp,"timestamp/I");
    //tree4->Branch("serialnumber",&serialnumber,"serialnumber/I");
    tree4->Branch("freqsetting",&event2.freqsetting,"freqsetting/I");
    tree4->Branch("triggerTime",&event2.triggerTime,"triggerTime/g");
    for(int i=0; i<8; i++) tree4->Branch(Form("Channel%d",i),"TH1D",&(event2.waveforms[i]));   
    
    int remInd1 = remove1.size() > 0 ? 0 : -1;
    int remInd2 = remove2.size() > 0 ? 0 : -1;
    cout << "****************************************Saving MIDAS data 1****************************************" << endl;
    for(int i = 0; i < ent1; i++){
        if(!((i+1)%10000)) cout << "    Processing event: " << i+1 << endl;
        tree1->GetEntry(i);
        if(remInd1 >=0){
            if(i == remove1.at(remInd1)){
                if(remInd1 < remove1.size()-1) remInd1++;
                continue;
            }
        }
        tree3->Fill();
    }
    cout << "****************************************Saving MIDAS data 2****************************************" << endl;
    for(int i = 0; i < ent2; i++){
        if(!((i+1)%10000)) cout << "    Processing event: " << i+1 << endl;
        tree2->GetEntry(i);
        if(remInd2 >=0){
            if(i == remove2.at(remInd2)){
                if(remInd2 < remove2.size()-1) remInd2++;
                continue;  
            }
        }
        tree4->Fill();
    }
    tree3->Write();
    tree4->Write();
    
    outFileData.Close();*/
}


